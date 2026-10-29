#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int x = unknown();
  if (!(x==1 || x==2)) return 0;
  while (unknown()) {
    if(x==1) x=2;
    else if (x==2) x=1;
  }
  //@ assert(x<=8);
  return 0;
}
