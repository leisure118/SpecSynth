#include <assert.h>
int main() {
  int i = 0;
  while (1) {
    i++;
    int j = 0;
    while (j < 10) {
      //@ assert(0 <= i);
      //@ assert(i <= 10);
      j++;
    }
    if (i > 9)
      i = 0;
  }
  return 0;
}
