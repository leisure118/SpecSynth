/* Auto-generated minimal verifiable slice */
/* Target function: main */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


static const u8 null_encoded_val[] = { 0x05, 0x00 };

int main();

/* --- Dependency: parse_null (stub) --- */
/* TODO: add ACSL contract here */
int parse_null(const u8 *buf, u32 len, u32 *parsed);

/* === Target: main === */
int main() {
  const u8 b[] = { 0x05, 0x00 };
  u32 parsed;
  int ret = parse_null(b, sizeof(null_encoded_val), &parsed);
  //@ assert parsed == sizeof(null_encoded_val);
  //@ assert ret == 0;
  return 0;
}
