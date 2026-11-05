/*@
  assigns \everything;
*/
int main()
{
  int i;
  int N=100000;
  int a[N];
  int b[N];
  int c[N];
  //@ assert \separated(a+(0 .. N-1), b+(0 .. N-1));
  //@ assert \separated(a+(0 .. N-1), c+(0 .. N-1));
  //@ assert \separated(b+(0 .. N-1), c+(0 .. N-1));
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> a[j] == 1 && b[j] == 2;
    loop assigns i, a[0 .. N-1], b[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++) {
    a[i]=1;
    b[i]=2;
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < N ==> a[j] == 1 && b[j] == 2;
    loop invariant \forall integer j; 0 <= j < i ==> c[j] == 3;
    loop assigns i, c[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    //@ assert(a[i] == 1 && b[i] == 2);
    c[i]=a[i]+b[i];
    //@ assert(c[i] == 3);
  }
  /*@
    loop invariant 1 <= i <= N;
    loop invariant \forall integer j; 0 <= j < N ==> c[j] == 3;
    loop invariant i < N ==> c[i] == 3;
    loop assigns i;
    loop variant N - i;
  */
  for(i=1;i<N;i++){
    //@ assert(c[i] >= 3);
  }
  return 0;
}