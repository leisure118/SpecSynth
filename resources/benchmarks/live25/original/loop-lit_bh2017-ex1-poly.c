#include <assert.h>
int main() {
  int i = 0;
  while (i < 4) {
    int j = 0;
    while (j < 3) {
      i++;
      j += 2;
      //@ assert(0 <= j);
      //@ assert(j <= 2 * i);
      //@ assert(2 * i <= j + 6);
      //@ assert(j <= 4);
    }
    //@ assert(0 <= j);
    //@ assert(j <= 2 * i);
    //@ assert(2 * i <= j + 6);
    //@ assert(j <= 4);
    i = i - j / 2 + 1;
  }
  return 0;
}
