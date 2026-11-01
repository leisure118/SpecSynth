#define SIZE 1000
#include <assert.h>
int main()
{
  unsigned int array[SIZE];
  unsigned int index;
  /*@
    loop invariant 0 <= index <= SIZE;
    loop invariant \forall integer j; 0 <= j < index ==> array[j] == (j % 2);
    loop assigns index, array[0 .. SIZE-1];
    loop variant SIZE - index;
  */
  for (index = 0; index < SIZE; index++) {
    array[index] = (index % 2);
  }
  /*@
    loop invariant 0 <= index <= SIZE;
    loop invariant \forall integer j; 0 <= j < SIZE ==> array[j] == (j % 2);
    loop assigns index;
    loop variant SIZE - index;
  */
  for (index = 0; index < SIZE; index++) {
    if (index % 2 == 0) {
      //@ assert(array[index] == 0);
    } else {
      //@ assert(array[index] != 0);
    }
  }
}
