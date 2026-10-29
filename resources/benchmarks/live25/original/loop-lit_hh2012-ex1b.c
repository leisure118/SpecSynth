#include <assert.h>
int main() {
  int i = 0;
  while (i < 100) {
    int j = 0;
    while (j < 100) {
      j++;
      //@ assert(j <= 100);
    }
    //@ assert(j == 100);
    i++;
    //@ assert(i <= 100);
  }
  //@ assert(i == 100);
  return 0;
}
