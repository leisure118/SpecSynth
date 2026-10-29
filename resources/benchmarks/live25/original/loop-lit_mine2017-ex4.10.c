#include <assert.h>
int main() {
  int v = 1; 
  while (v <= 50) {
    //@ assert(1 <= v);
    v += 2;
    //@ assert(v <= 52);
  }
  //@ assert(51 <= v);
  //@ assert(v <= 52);
  return 0;
}
