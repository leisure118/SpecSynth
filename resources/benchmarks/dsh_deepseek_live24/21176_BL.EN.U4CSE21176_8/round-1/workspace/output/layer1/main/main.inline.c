/* Auto-generated minimal verifiable slice */
/* Target function: main */
/* Mode: inline */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


extern int sqrt();

double Sqrt(double x);
int main();

double Sqrt(double x){	
	return sqrt(x);
}

/* === Target: main === */
int main(){
	double x = 9;
	double y;
	y = Sqrt(x);
	//@assert y == sqrt(x); 
	return 0;
}
