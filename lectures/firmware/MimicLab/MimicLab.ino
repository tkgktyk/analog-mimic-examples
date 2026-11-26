// SPDX-License-Identifier: MIT
/**
 * MimicLab: a measuring instrument for the lectures, on an Arduino UNO R4.
 *
 *   - Function generator (FG): sine, square, triangle or DC on the DAC (A0, 12 bit)
 *   - 2-channel scope: CH1 = A1 (the module input), CH2 = A2 (the module output), 14 bit
 *   - Control of the Analog Mimic module through the AnalogMimic library
 *
 * Controlled from a PC over the serial port with text commands (one per line), e.g.
 *   id
 *   fg sine 100 1.0
 *   mimic setFilter1stLPF 100
 *   scope capture 2000 1
 * Type "help" in the serial monitor for the list. See lectures/README.md for the wiring.
 *
 * Protocol (proto 1):
 *   - Every command gets exactly one line: "ok ..." or "err <reason>".
 *     Lines starting with "#" are for people and are ignored by the Python library.
 *   - "scope capture" answers "ok bin <bytes> <channels> <points> <fs>", then exactly <bytes>
 *     bytes (uint16 little endian, CH1 and CH2 interleaved, ADC codes), then a line "end".
 *
 * Prototype: a single 20 kHz timer interrupt updates the DAC and reads the ADC (the
 * interrupt latency moves the sampling instants by a few microseconds).
 */
#include <AnalogMimic.h>
#include <AnalogMimicExperimental.h>  // modes of the next releases (lectures of chapter 4 and later)
#include <FspTimer.h>
#include <strings.h>

// ---- Settings -------------------------------------------------------------------------

constexpr char VERSION[] = "0.1.4";
constexpr int PROTOCOL = 1;
constexpr uint32_t BAUD = 1000000;   // ignored by the UNO R4 Minima (native USB); used by the WiFi
constexpr float TICK_HZ = 20000.0f;  // DAC update and ADC sampling rate
constexpr float VREF_V = 5.0f;       // full scale of the DAC and the ADC (AVCC)
constexpr int DAC_BITS = 12;
constexpr int ADC_BITS = 14;
constexpr uint16_t DAC_MAX = (1u << DAC_BITS) - 1;
// Points per channel (2 channels x 2 bytes each: 8 KB). The cores of the UNO R4 (1.6.0)
// keep 8 KB of the 32 KB RAM for the heap, and 4000 points (16 KB) no longer fit.
constexpr uint16_t MAX_POINTS = 2000;

volatile uint16_t *const DAC_DATA = (uint16_t *)0x4005E000;  // DAC12 DADR0 (pin A0)

MimicExperimental<Mimic0x> mimic(MIMIC_VDD_5V);  // Mimic0x plus the experimental modes
bool mimicReady = false;

// ---- Function generator (DDS) -----------------------------------------------------------

enum Wave : uint8_t { WAVE_DC = 0, WAVE_SINE, WAVE_SQUARE, WAVE_TRIANGLE };
const char *const WAVE_NAMES[] = { "dc", "sine", "square", "triangle" };

constexpr int SINE_BITS = 10;
int16_t sineTable[1 << SINE_BITS];  // -32767 .. 32767

FspTimer tickTimer;
volatile uint8_t fgWave = WAVE_DC;
volatile uint32_t fgIncrement = 0;  // phase increment per tick (2^32 = one period)
volatile int32_t fgAmpCode = 0;     // peak amplitude in DAC codes
volatile int32_t fgOffsetCode = 2048;
uint32_t fgPhase = 0;
float fgFreqHz = 0.0f, fgAmpV = 0.0f, fgOffsetV = VREF_V / 2;

// ---- Scope ----------------------------------------------------------------------------

enum CaptureState : uint8_t { CAP_IDLE = 0, CAP_ARMED, CAP_RUN, CAP_DONE };
uint16_t captureBuf[2 * MAX_POINTS];
volatile uint8_t capState = CAP_IDLE;
volatile bool capSync = true;
volatile uint16_t capPoints = 0, capIndex = 0, capDivider = 1, capDivCount = 0;
uint8_t adcCh1 = 0, adcCh2 = 0;  // ADC channels (ANxxx) of A1 and A2

// ---- Interrupt: FG and scope ----------------------------------------------------------

static inline void readAdc(uint16_t *dst) {
  while (R_ADC0->ADCSR_b.ADST) {}  // a discarded scan (onTick) has ended long ago
  R_ADC0->ADCSR_b.ADST = 1;  // single scan of the two channels
  while (R_ADC0->ADCSR_b.ADST) {}
  dst[0] = R_ADC0->ADDR[adcCh1];
  dst[1] = R_ADC0->ADDR[adcCh2];
}

void onTick(timer_callback_args_t *) {
  uint32_t prev = fgPhase;
  fgPhase += fgIncrement;
  bool phaseZero = fgPhase < prev;  // the phase wrapped: start of a period

  int32_t s;  // -32767 .. 32767
  switch (fgWave) {
    case WAVE_SINE:
      s = sineTable[fgPhase >> (32 - SINE_BITS)];
      break;
    case WAVE_SQUARE:  // high in the first half of the period
      s = (fgPhase & 0x80000000u) ? -32767 : 32767;
      break;
    case WAVE_TRIANGLE: {  // centre and rising at phase 0
      uint32_t q = (fgPhase + 0x40000000u) >> 16;  // 0 .. 65535
      int32_t a = (q < 32768) ? (int32_t)q : (int32_t)(65535 - q);
      s = 2 * a - 32767;
      break;
    }
    default:
      s = 0;
      break;
  }
  int32_t code = fgOffsetCode + ((fgAmpCode * s) >> 15);
  if (code < 0) code = 0;
  if (code > DAC_MAX) code = DAC_MAX;
  *DAC_DATA = (uint16_t)code;

  bool sampled = false;
  switch (capState) {
    case CAP_ARMED:
      if (capSync && !phaseZero) break;
      capState = CAP_RUN;
      capIndex = 0;
      capDivCount = 0;
      // the first point is taken at this tick
      __attribute__((fallthrough));
    case CAP_RUN:
      if (capDivCount == 0) {
        readAdc(&captureBuf[2 * capIndex]);
        sampled = true;
        if (++capIndex >= capPoints) capState = CAP_DONE;
      }
      if (++capDivCount >= capDivider) capDivCount = 0;
      break;
    default:
      break;
  }
  // When no point is taken at this tick, start a scan anyway and discard it (no waiting):
  // the ADC loads the inputs the same way all the time, at every sampling rate and between
  // captures. Each scan connects the sampling capacitor (charged to the other channel) to
  // the pin, so a high-impedance source (a finger) drifts while the ADC is idle and jumps
  // at the start of the next capture. The scan ends long before the next tick.
  if (!sampled) R_ADC0->ADCSR_b.ADST = 1;
}

// ---- Setup ----------------------------------------------------------------------------

// The ADC channel the core selects for a pin (read back from the scan register).
// Channels found before (if the core leaves them selected) are excluded.
uint8_t adcChannelOf(pin_size_t pin, uint32_t exclude = 0) {
  (void)analogRead(pin);
  uint32_t mask = R_ADC0->ADANSA[0] | ((uint32_t)R_ADC0->ADANSA[1] << 16);
  if (mask & ~exclude) mask &= ~exclude;
  return mask ? (uint8_t)__builtin_ctz(mask) : 0;
}

void setupAdc() {
  analogReadResolution(ADC_BITS);
  adcCh1 = adcChannelOf(A1);
  adcCh2 = adcChannelOf(A2, 1ul << adcCh1);
  // The module output has a 470 ohm series resistor: longest sampling time (about 5.3 us)
  for (uint8_t ch = 0; ch < 8; ch++) R_ADC0->ADSSTR[ch] = 255;
  // Single scan of both channels, started by software (ADST)
  R_ADC0->ADCSR_b.ADCS = 0;
  R_ADC0->ADANSA[0] = 0;
  R_ADC0->ADANSA[1] = 0;
  uint32_t mask = (1ul << adcCh1) | (1ul << adcCh2);
  R_ADC0->ADANSA[0] = (uint16_t)(mask & 0xFFFF);
  R_ADC0->ADANSA[1] = (uint16_t)(mask >> 16);
}

bool setupTick() {
  for (int i = 0; i < (1 << SINE_BITS); i++) {
    sineTable[i] = (int16_t)lroundf(32767.0f * sinf(2.0f * PI * i / (1 << SINE_BITS)));
  }
  analogWriteResolution(DAC_BITS);
  analogWrite(A0, 0);  // enables the DAC on A0
  uint8_t type = 0;
  int8_t channel = FspTimer::get_available_timer(type);
  if (channel < 0) return false;
  if (!tickTimer.begin(TIMER_MODE_PERIODIC, type, channel, TICK_HZ, 50.0f, onTick)) return false;
  tickTimer.setup_overflow_irq(0);  // highest priority: USB and serial must not delay the DAC
  tickTimer.open();
  tickTimer.start();
  return true;
}

bool beginMimic() {
  static bool wireStarted = false;
  if (wireStarted) Wire.end();  // a stuck Wire recovers by starting it again
  Wire.begin();
  wireStarted = true;
  delay(10);
  mimicReady = mimic.begin();
  return mimicReady;
}

// ---- Commands -------------------------------------------------------------------------

constexpr int MAX_TOKENS = 8;
char *tokens[MAX_TOKENS];
int numTokens = 0;
char out[96];

int32_t voltsToDac(float v) { return (int32_t)lroundf(v / VREF_V * (DAC_MAX + 1)); }

// A number, or a keyword: pos / neg (polarity), on / off, true / false,
// sine / triangle / square / sawtooth (oscillator waveform), white / pink (noise color)
bool parseArg(const char *s, float *v) {
  if (!strcasecmp(s, "sine")) { *v = MIMIC_OSC_WAVE_SINE; return true; }
  if (!strcasecmp(s, "triangle")) { *v = MIMIC_OSC_WAVE_TRIANGLE; return true; }
  if (!strcasecmp(s, "square")) { *v = MIMIC_OSC_WAVE_SQUARE; return true; }
  if (!strcasecmp(s, "sawtooth")) { *v = MIMIC_OSC_WAVE_SAWTOOTH; return true; }
  if (!strcasecmp(s, "white")) { *v = MIMIC_NOISE_WHITE; return true; }
  if (!strcasecmp(s, "pink")) { *v = MIMIC_NOISE_PINK; return true; }
  if (!strcasecmp(s, "pos") || !strcasecmp(s, "positive")) { *v = MIMIC_POLARITY_POSITIVE; return true; }
  if (!strcasecmp(s, "neg") || !strcasecmp(s, "negative")) { *v = MIMIC_POLARITY_NEGATIVE; return true; }
  if (!strcasecmp(s, "on") || !strcasecmp(s, "true")) { *v = 1; return true; }
  if (!strcasecmp(s, "off") || !strcasecmp(s, "false")) { *v = 0; return true; }
  char *end;
  *v = strtof(s, &end);
  return end != s && *end == '\0';
}

// Floats are printed with Serial.print (printf of the core may not format floats)
void printKey(const char *key, float v, int digits) { Serial.print(' '); Serial.print(key); Serial.print('='); Serial.print(v, digits); }

void reply(const char *s) { Serial.print("ok"); if (s && *s) { Serial.print(' '); Serial.print(s); } Serial.print('\n'); }
void fail(const char *s) { Serial.print("err "); Serial.print(s); Serial.print('\n'); }

void cmdId() {
  char date[12] = "none";
  if (mimicReady) snprintf(date, sizeof(date), "%08lx", (unsigned long)mimic.getBuildDate());
  snprintf(out, sizeof(out), "ok MimicLab proto=%d ver=%s fs=%lu dac=%d adc=%d maxpts=%u mimic=%s",
           PROTOCOL, VERSION, (unsigned long)TICK_HZ, DAC_BITS, ADC_BITS, (unsigned)MAX_POINTS, date);
  Serial.print(out);
  printKey("vref", VREF_V, 3);
  Serial.print('\n');
}

void cmdHelp() {
  Serial.print(
    "# id                                   instrument and module (mimic=none if not found)\n"
    "# fg                                   current FG setting\n"
    "# fg sine|square|triangle <Hz> <Vpeak> [Voffset]   (offset defaults to 2.5 V)\n"
    "# fg dc <V>\n"
    "# scope capture <points> [divider] [sync|free]     fs = 20000 / divider;\n"
    "#                                      sync starts at FG phase 0 (default unless dc)\n"
    "# mimic begin                          connect to the module again\n"
    "# mimic list                           methods of the library\n"
    "# mimic <method> [args...]             e.g. mimic setFilter1stLPF 100\n"
    "#                                      args: numbers, pos / neg, on / off\n");
  reply(nullptr);
}

// ok <wave> freq=<Hz> amp=<Vpeak> offset=<V>  (freq is the actual frequency of the DDS)
void reportFg() {
  Serial.print("ok ");
  Serial.print(WAVE_NAMES[fgWave]);
  printKey("freq", fgFreqHz, 6);
  printKey("amp", fgAmpV, 4);
  printKey("offset", fgOffsetV, 4);
  Serial.print('\n');
}

void cmdFg() {
  if (numTokens == 1) { reportFg(); return; }
  const char *w = tokens[1];
  float a[3];
  for (int i = 2; i < numTokens; i++) {
    if (i - 2 >= 3 || !parseArg(tokens[i], &a[i - 2])) { fail("bad argument"); return; }
  }
  int n = numTokens - 2;
  if (!strcasecmp(w, "dc")) {
    if (n != 1) { fail("usage: fg dc <V>"); return; }
    fgWave = WAVE_DC;
    fgFreqHz = 0; fgAmpV = 0; fgOffsetV = a[0];
  } else {
    uint8_t wave;
    if (!strcasecmp(w, "sine")) wave = WAVE_SINE;
    else if (!strcasecmp(w, "square")) wave = WAVE_SQUARE;
    else if (!strcasecmp(w, "triangle")) wave = WAVE_TRIANGLE;
    else { fail("unknown wave"); return; }
    if (n < 2 || n > 3) { fail("usage: fg <wave> <Hz> <Vpeak> [Voffset]"); return; }
    if (a[0] < 0 || a[0] > TICK_HZ / 2) { fail("frequency out of range"); return; }
    uint32_t inc = (uint32_t)((double)a[0] * 4294967296.0 / TICK_HZ);
    fgFreqHz = (float)((double)inc * TICK_HZ / 4294967296.0);  // actual frequency
    fgAmpV = a[1];
    fgOffsetV = (n == 3) ? a[2] : VREF_V / 2;
    noInterrupts();
    fgWave = wave;
    fgIncrement = inc;
    interrupts();
  }
  noInterrupts();
  fgAmpCode = voltsToDac(fgAmpV);
  fgOffsetCode = voltsToDac(fgOffsetV);
  interrupts();
  reportFg();
}

void cmdScope() {
  if (numTokens < 2) { fail("usage: scope capture <points> [divider] [sync|free]"); return; }
  if (strcasecmp(tokens[1], "capture")) { fail("unknown scope command"); return; }
  if (numTokens < 3) { fail("usage: scope capture <points> [divider] [sync|free]"); return; }
  long points = atol(tokens[2]);
  long divider = (numTokens >= 4) ? atol(tokens[3]) : 1;
  bool sync = (fgWave != WAVE_DC && fgIncrement != 0);
  if (numTokens >= 5) {
    if (!strcasecmp(tokens[4], "free")) sync = false;
    else if (!strcasecmp(tokens[4], "sync")) {
      if (fgWave == WAVE_DC || fgIncrement == 0) { fail("sync needs an FG wave"); return; }
      sync = true;
    } else { fail("trigger must be sync or free"); return; }
  }
  if (points < 1 || points > MAX_POINTS) {
    snprintf(out, sizeof(out), "points out of range (1 - %u)", (unsigned)MAX_POINTS);
    fail(out);
    return;
  }
  if (divider < 1 || divider > 65535) { fail("divider out of range (1 - 65535)"); return; }

  // Timeout: one FG period (waiting for phase 0) + the capture + margin
  float waitS = (float)points * divider / TICK_HZ + 0.5f;
  if (sync) waitS += 1.0f / fgFreqHz;
  noInterrupts();
  capPoints = (uint16_t)points;
  capDivider = (uint16_t)divider;
  capSync = sync;
  capState = CAP_ARMED;
  interrupts();
  uint32_t start = millis();
  while (capState != CAP_DONE) {
    if (millis() - start > (uint32_t)(waitS * 1000.0f)) {
      capState = CAP_IDLE;
      fail("capture timeout");
      return;
    }
  }
  uint32_t bytes = (uint32_t)points * 2 * sizeof(uint16_t);
  snprintf(out, sizeof(out), "ok bin %lu 2 %ld ", (unsigned long)bytes, points);
  Serial.print(out);
  Serial.print(TICK_HZ / divider, 3);
  Serial.print('\n');
  const uint8_t *p = (const uint8_t *)captureBuf;  // little endian, CH1 and CH2 interleaved
  uint32_t lastProgress = millis();
  for (uint32_t sent = 0; sent < bytes;) {
    uint32_t chunk = bytes - sent;
    if (chunk > 256) chunk = 256;
    size_t n = Serial.write(p + sent, chunk);
    sent += n;
    if (n) lastProgress = millis();
    else if (millis() - lastProgress > 2000) break;  // nobody reads the port
  }
  Serial.print("end\n");
  capState = CAP_IDLE;
}

// ---- Mimic: library methods by name ---------------------------------------------------

typedef void (*MimicFn)(const float *a, int n);
struct MimicMethod {
  const char *name;
  uint8_t minArgs, maxArgs;
  MimicFn fn;
};

#define U8(x) ((uint8_t)lroundf(x))
#define U16(x) ((uint16_t)lroundf(x))
const MimicMethod MIMIC_METHODS[] = {
  // Global settings
  { "setOutputOpen", 1, 1, [](const float *a, int) { mimic.setOutputOpen(a[0] != 0); } },
  { "setOutputInverted", 1, 1, [](const float *a, int) { mimic.setOutputInverted(a[0] != 0); } },
  { "setDecimation", 1, 1, [](const float *a, int) { mimic.setDecimation(U8(a[0])); } },
  { "setOutputOffset", 1, 1, [](const float *a, int) { mimic.setOutputOffset(a[0]); } },
  { "setVref", 1, 1, [](const float *a, int) { mimic.setVref(a[0]); } },
  // Modes released in the library
  { "setBypassDSP", 0, 0, [](const float *, int) { mimic.setBypassDSP(); } },
  { "setPGA", 1, 1, [](const float *a, int) { mimic.setPGA(a[0]); } },
  { "setFilter1stLPF", 1, 1, [](const float *a, int) { mimic.setFilter1stLPF(a[0]); } },
  { "setFilter1stHPF", 1, 1, [](const float *a, int) { mimic.setFilter1stHPF(a[0]); } },
  { "setFilter1stAPF", 1, 1, [](const float *a, int) { mimic.setFilter1stAPF(a[0]); } },
  { "setFilterBiquadUnity", 0, 0, [](const float *, int) { mimic.setFilterBiquadUnity(); } },
  { "setFilterBiquadLPF", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setFilterBiquadLPF(a[0], a[1]) : mimic.setFilterBiquadLPF(a[0]); } },
  { "setFilterBiquadHPF", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setFilterBiquadHPF(a[0], a[1]) : mimic.setFilterBiquadHPF(a[0]); } },
  { "setFilterBiquadBPF", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setFilterBiquadBPF(a[0], a[1]) : mimic.setFilterBiquadBPF(a[0]); } },
  { "setFilterBiquadNotch", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setFilterBiquadNotch(a[0], a[1]) : mimic.setFilterBiquadNotch(a[0]); } },
  { "setFilterBiquadAPF", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setFilterBiquadAPF(a[0], a[1]) : mimic.setFilterBiquadAPF(a[0]); } },
  { "setComparatorWindow", 2, 2, [](const float *a, int) { mimic.setComparatorWindow(a[0], a[1]); } },
  { "setComparatorSchmitt", 2, 2, [](const float *a, int) { mimic.setComparatorSchmitt(a[0], a[1]); } },
  { "setEnvelopeFollower", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setEnvelopeFollower(a[0], U8(a[1])) : mimic.setEnvelopeFollower(a[0]); } },
  { "setPeakHold", 0, 1, [](const float *a, int n) { n > 0 ? mimic.setPeakHold(U8(a[0])) : mimic.setPeakHold(); } },
  { "setClipper", 2, 2, [](const float *a, int) { mimic.setClipper(a[0], a[1]); } },
  { "setSoftClipper", 2, 2, [](const float *a, int) { mimic.setSoftClipper(a[0], a[1]); } },
  { "setConstantVoltage", 1, 1, [](const float *a, int) { mimic.setConstantVoltage(a[0]); } },
  { "setIntegrator", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setIntegrator(a[0], a[1]) : mimic.setIntegrator(a[0]); } },
  { "setDifferentiator", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setDifferentiator(a[0], a[1]) : mimic.setDifferentiator(a[0]); } },
  { "setRectifierHalf", 0, 1, [](const float *a, int n) { n > 0 ? mimic.setRectifierHalf(U8(a[0])) : mimic.setRectifierHalf(); } },
  { "setRectifierFull", 0, 1, [](const float *a, int n) { n > 0 ? mimic.setRectifierFull(U8(a[0])) : mimic.setRectifierFull(); } },
  // Time: sample & hold, slew rate, delay (experimental in the library 0.2)
  { "setSampleAndHold", 1, 1, [](const float *a, int) { mimic.setSampleAndHold(a[0]); } },
  { "setTrackAndHold", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setTrackAndHold(a[0], a[1]) : mimic.setTrackAndHold(a[0]); } },
  { "setSlewRateLimiter", 1, 1, [](const float *a, int) { mimic.setSlewRateLimiter(a[0]); } },
  { "setDigitalDelay", 1, 1, [](const float *a, int) { mimic.setDigitalDelay(U16(a[0])); } },
  // Signal sources and modulators (experimental in the library 0.2)
  { "setOscillator", 2, 3, [](const float *a, int n) { n > 2 ? mimic.setOscillator(a[0], a[1], U8(a[2])) : mimic.setOscillator(a[0], a[1]); } },
  { "setVco", 3, 4, [](const float *a, int n) { n > 3 ? mimic.setVco(a[0], a[1], a[2], U8(a[3])) : mimic.setVco(a[0], a[1], a[2]); } },
  { "setAmModulator", 3, 4, [](const float *a, int n) { n > 3 ? mimic.setAmModulator(a[0], a[1], a[2], U8(a[3])) : mimic.setAmModulator(a[0], a[1], a[2]); } },
  { "setRingModulator", 1, 3, [](const float *a, int n) {
      if (n > 2) mimic.setRingModulator(a[0], a[1], U8(a[2]));
      else if (n > 1) mimic.setRingModulator(a[0], a[1]);
      else mimic.setRingModulator(a[0]); } },
  { "setPwmModulator", 2, 3, [](const float *a, int n) { n > 2 ? mimic.setPwmModulator(a[0], a[1], U8(a[2])) : mimic.setPwmModulator(a[0], a[1]); } },
  { "setVfConverter", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setVfConverter(a[0], a[1]) : mimic.setVfConverter(a[0]); } },
  { "setNoise", 1, 2, [](const float *a, int n) { n > 1 ? mimic.setNoise(a[0], U8(a[1])) : mimic.setNoise(a[0]); } },
};
#undef U8
#undef U16

void cmdMimic() {
  if (numTokens < 2) { fail("usage: mimic <method> [args...]"); return; }
  const char *m = tokens[1];
  if (!strcasecmp(m, "list")) {
    for (const MimicMethod &mm : MIMIC_METHODS) {
      Serial.print("# "); Serial.print(mm.name);
      Serial.print(" ("); Serial.print(mm.minArgs);
      if (mm.maxArgs != mm.minArgs) { Serial.print('-'); Serial.print(mm.maxArgs); }
      Serial.print(" args)\n");
    }
    Serial.print("# getStatus getInputVolts getAdcValue getBuildDate getUnitId\n");
    reply(nullptr);
    return;
  }
  if (!strcasecmp(m, "begin")) {
    if (beginMimic()) reply(nullptr); else fail("module not found");
    return;
  }
  if (!mimicReady) { fail("module not found (mimic begin to retry)"); return; }

  // Getters
  if (!strcasecmp(m, "getStatus")) { snprintf(out, sizeof(out), "%u", mimic.getStatus()); reply(out); return; }
  if (!strcasecmp(m, "getInputVolts")) { Serial.print("ok "); Serial.print(mimic.getInputVolts(), 5); Serial.print('\n'); return; }
  if (!strcasecmp(m, "getAdcValue")) {
    uint8_t seq;
    uint16_t v = mimic.getAdcValue(&seq);
    snprintf(out, sizeof(out), "%u %u", v, seq);
    reply(out);
    return;
  }
  if (!strcasecmp(m, "getBuildDate")) { snprintf(out, sizeof(out), "%08lx", (unsigned long)mimic.getBuildDate()); reply(out); return; }
  if (!strcasecmp(m, "getUnitId")) { snprintf(out, sizeof(out), "%08lx", (unsigned long)mimic.getUnitId()); reply(out); return; }

  // Setters
  for (const MimicMethod &mm : MIMIC_METHODS) {
    if (strcasecmp(m, mm.name)) continue;
    int n = numTokens - 2;
    if (n < mm.minArgs || n > mm.maxArgs) { fail("wrong number of arguments"); return; }
    float a[4];
    for (int i = 0; i < n; i++) {
      if (!parseArg(tokens[2 + i], &a[i])) { fail("bad argument"); return; }
    }
    mm.fn(a, n);
    reply(nullptr);
    return;
  }
  fail("unknown method (mimic list)");
}

// ---- Main -----------------------------------------------------------------------------

void execute(char *line) {
  numTokens = 0;
  for (char *t = strtok(line, " \t"); t && numTokens < MAX_TOKENS; t = strtok(nullptr, " \t")) {
    tokens[numTokens++] = t;
  }
  if (numTokens == 0) return;
  const char *c = tokens[0];
  if (!strcasecmp(c, "id")) cmdId();
  else if (!strcasecmp(c, "help")) cmdHelp();
  else if (!strcasecmp(c, "fg")) cmdFg();
  else if (!strcasecmp(c, "scope")) cmdScope();
  else if (!strcasecmp(c, "mimic")) cmdMimic();
  else fail("unknown command (help)");
}

void setup() {
  Serial.begin(BAUD);
  setupAdc();
  bool tickOk = setupTick();
  beginMimic();
  Serial.print(tickOk ? "# MimicLab ready\n" : "# MimicLab: no timer available\n");
}

void loop() {
  static char line[96];
  static size_t len = 0;
  static bool overflow = false;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      line[len] = '\0';
      if (overflow) fail("line too long"); else execute(line);
      len = 0;
      overflow = false;
    } else if (len < sizeof(line) - 1) {
      line[len++] = c;
    } else {
      overflow = true;
    }
  }
}
