#include<limits.h>
/*@
assigns \nothing;
ensures 1 < \result < INT_MAX;
*/
int unknown();
int main()
{
  int S=unknown();
  //@ assert(S>1);
  long long i;
  long long a[S];
  /*@
    loop invariant 0 <= i <= S;
    loop invariant \forall integer j; 0 <= j < i ==> a[j] == (j-1)*(j+1);
    loop assigns i, a[0 .. S-1];
    loop variant S - i;
  */
  for(i=0;i<S;i++)
    a[i]=((i-1)*(i+1));
  /*@
    loop invariant 0 <= i <= S;
    loop invariant \forall integer j; 0 <= j < i ==> a[j] == -1;
    loop invariant \forall integer j; i <= j < S ==> a[j] == (j-1)*(j+1);
    loop assigns i, a[0 .. S-1];
    loop variant S - i;
  */
  for(i=0;i<S;i++)
    a[i]=a[i]-(i*i);
  /*@
    loop invariant 0 <= i <= S;
    loop invariant \forall integer j; 0 <= j < S ==> a[j] == -1;
    loop assigns i;
    loop variant S - i;
  */
  for(i=0;i<S;i++){
    //@ assert(a[i]==-1);
  }
  return 0;
}
