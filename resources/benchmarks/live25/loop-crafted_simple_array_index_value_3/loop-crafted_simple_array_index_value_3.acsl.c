#define SIZE 10000
#include <assert.h>
int main()
{
  unsigned int array[SIZE];
  unsigned int index = 0;
  unsigned int tmp = 0;
  /*@
    loop invariant 0 <= index <= SIZE;
    loop invariant \forall integer j; 0 <= j < index ==> array[j] == 2*j;
    loop invariant tmp == 2*index;
    loop assigns index, tmp, array[0 .. SIZE-1];
    loop variant SIZE - index;
  */
  while (index < SIZE) {
    array[index] = tmp;
    index = index + 1;
    tmp = tmp + 2;
  }
  /*@
    loop invariant 0 <= index <= SIZE;
    loop invariant \forall integer j; 0 <= j < SIZE ==> array[j] == 2*j;
    loop assigns index;
    loop variant SIZE - index;
  */
  for (index = 0; index < SIZE; index++) {
     //@ assert((array[index] == 2*index) || (array[index] == 0));
  }
}
