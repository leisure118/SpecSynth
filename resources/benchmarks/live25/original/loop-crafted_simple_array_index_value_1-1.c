#define SIZE 1000
#include <assert.h>
int main()
{
  unsigned int array[SIZE];
  unsigned int index;
  for (index = 0; index < SIZE; index++) {
    array[index] = (index % 2);
  }
  for (index = 0; index < SIZE; index++) {
    if (index % 2 == 0) {
      //@ assert(array[index] == 0);
    } else {
      //@ assert(array[index] != 0);
    }
  }
}
