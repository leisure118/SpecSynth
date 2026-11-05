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
/*@ loop invariant 0 <= i < S;
loop invariant \forall integer j; 0 <= j < i ==> acopy[2*S - (j+1)] == a[2*S - (j+1)] && acopy[j] == a[j];
loop assigns i, acopy[0 .. 2*S-1];
loop variant S - i;
*/
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
