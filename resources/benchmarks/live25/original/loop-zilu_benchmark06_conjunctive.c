#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int j = unknown();
  int i = unknown();
  int x = unknown();
  int y = unknown();
  int k = unknown();
  j=0;
  if (!(x+y==k)) return 0;
  while (unknown()) {
    if(j==i) {x++;y--;} else {y++;x--;} j++;
  }
  //@ assert(x+y==k);
  return 0;
}
