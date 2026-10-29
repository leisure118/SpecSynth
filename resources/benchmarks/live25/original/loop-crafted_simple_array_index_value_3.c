#define SIZE 10000
#include <assert.h>
int main()
{
  unsigned int array[SIZE];
  unsigned int index = 0;
  unsigned int tmp = 0;
  while (index < SIZE) {
    array[index] = tmp;
    index = index + 1;
    tmp = tmp + 2;
  }
  for (index = 0; index < SIZE; index++) {
     //@ assert((array[index] == 2*index) || (array[index] == 0));
  }
}
