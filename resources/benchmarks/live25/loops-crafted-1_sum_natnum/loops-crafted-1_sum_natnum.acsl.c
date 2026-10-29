#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int SIZE = 40000; 
int main() {
  int i;
  unsigned long long sum;
  i = 0, sum =0; 
  /*@
    loop invariant 0 <= i <= SIZE;
    loop invariant sum == i * (i + 1) / 2;
    loop assigns i, sum;
    loop variant SIZE - i;
  */
  while(i< SIZE){ 
      i = i + 1; 
      sum += i;
  }
  //@ assert( sum == ((SIZE *(SIZE+1))/2));
  return 0;
}
