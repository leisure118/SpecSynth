#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int i = unknown();
  int c = unknown();
  if (!(c==0 && i==0)) return 0;
  while (i<100) {
    c=c+i;
    i=i+1;
    if (i<=0) break;
  }
  //@ assert(c>=0);
  return 0;
}
