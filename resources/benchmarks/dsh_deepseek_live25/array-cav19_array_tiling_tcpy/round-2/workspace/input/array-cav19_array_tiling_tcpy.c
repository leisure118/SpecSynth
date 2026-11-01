#include<limits.h>
/*@
assigns \nothing;
ensures 1 < \result < INT_MAX/2;
*/
int unknown();
int main()
{
  int S=unknown();
  //@ assert(S>1);
  //@ assert(S < 1073741823);
  int i;
  int a[2*S];
  int acopy[2*S];
  for(i=0;i < S;i++) {
    acopy[2*S - (i+1)] = a[2*S - (i+1)];
    acopy[i] = a[i];
  }
  for(i=0;i<2*S;i++){
    //@ assert(acopy[i] == a[i]);
  }
  return 0;
}
