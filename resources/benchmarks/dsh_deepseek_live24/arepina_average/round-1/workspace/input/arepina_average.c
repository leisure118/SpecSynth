int average(int a, int b)
{
   int average = 0;
	int greater;
	int smaller;
	if (a > b) {
	   greater = a;
	   smaller = b;
	} else {
	   greater = b;
	   smaller = a;
	}
	if (a >= 0 && b >= 0) {
	   average = smaller + (greater - smaller) / 2;
	} else if (a < 0 && b < 0) {
	   average = greater + (smaller - greater) / 2;
	} else if ((a >= 0 && b <= 0) || (a <= 0 && b >= 0)) {
	   average = (a + b) / 2;
	}
   return average;
}
#ifdef OUT_OF_TASK
#include <stdio.h>
int main(void)
{
   int a = average(3,30);
   int b = average(-5,-20);
   int c = average(7,-10);
   int d = average(-2,15);
   //@ assert a == 16;
   //@ assert b == -13;
   //@ assert c == -3;
   //@ assert d == 8;
   return 0;
}
#endif