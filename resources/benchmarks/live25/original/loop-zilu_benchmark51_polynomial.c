#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int x = unknown();
  if (!((x>=0) && (x<=50))) return 0;
  while (unknown()) {
    if (x>50) x++;
    if (x == 0) { x ++;
    } else x--;
  }
  //@assert((x>=0) && (x<=50));
  return 0;
}
