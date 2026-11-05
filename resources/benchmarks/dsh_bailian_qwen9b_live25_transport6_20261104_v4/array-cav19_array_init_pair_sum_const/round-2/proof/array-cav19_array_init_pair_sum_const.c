/*@
  assigns \nothing;
*/
int main()
{
  int i;
  int N=100000;
  int a[N];
  int b[N];
  int c[N];
/*@ loop invariant 0 <= i <= 100000;
    loop invariant \forall integer k; 0 <= k < i ==> a[k] == 1 && b[k] == 2;
    loop assigns i, a[0 .. 99999], b[0 .. 99999];
    loop variant 100000 - i;
*/
  for(i=0;i<N;i++) {
    a[i]=1;
    b[i]=2;
  }
/*@ loop invariant 0 <= i <= 100000;
    loop invariant \forall integer k; 0 <= k < i ==> c[k] == a[k] + b[k];
    loop assigns i, c[0 .. 99999];
    loop variant 100000 - i;
*/
  for(i=0;i<N;i++){
    c[i]=a[i]+b[i];
  }
/*@ loop invariant 1 <= i <= 100000;
    loop assigns i;
    loop variant 100000 - i;
*/
  for(i=1;i<N;i++){
    //@ assert(c[i] >= 3);
  }
  return 0;
}
