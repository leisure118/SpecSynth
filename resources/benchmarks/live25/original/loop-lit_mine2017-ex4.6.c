#include <assert.h>
int main() {
  int x = 40;
  while (x != 0) {
    //@ assert(x <= 40);
    x--;
    //@ assert(x >= 0);
  }
  //@ assert(x == 0);
  return 0;
}
