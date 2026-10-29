#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int x = unknown();
  int y = unknown();
  if (!(x*y>=0)) return 0;
  while (unknown()) {
    if(x==0) {if (y>0) x++;
    else x--;} if(x>0) y++;
    else x--;
  }
  //@ assert(x*y>=0);
  return 0;
}
