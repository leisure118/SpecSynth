/*@
  assigns \nothing;
  ensures -100000 < \result < 100000;
*/
int unknown();
int N = 100000;
int main()
{
  int i;
  int a[N];
  int b[N];
  int c[N];
  int x= unknown();
  /*@ loop invariant 0 <= i <= N;
      loop invariant \forall integer j; 0 <= j < i ==> a[j] == -b[j];
      loop invariant \forall integer j; 0 <= j < i ==> -100000 < a[j] < 100000;
      loop assigns i, x, a[0 .. N-1], b[0 .. N-1];
      loop variant N - i;
  */
  for(i=0;i<N;i++) {
    x = unknown();
    //@ assert (x > -100000 && x < 100000);
    //@ assert -100000 < x < 100000;
    a[i]=x;
    b[i]=-x;
  }
  /*@ loop invariant 0 <= i <= N;
      loop invariant \forall integer j; 0 <= j < N ==> a[j] == -b[j];
      loop invariant \forall integer j; 0 <= j < i ==> a[j] == -b[j];
      loop invariant \forall integer j; 0 <= j < i ==> c[j] == 0;
      loop assigns i, c[0 .. N-1];
      loop variant N - i;
  */
  for(i=0;i<N;i++){
    //@ assert a[i] == -b[i];
    c[i]=a[i]+b[i];
  }
  /*@ loop invariant 1 <= i <= N;
      loop invariant \forall integer j; 0 <= j < N ==> c[j] == 0;
      loop assigns i;
      loop variant N - i;
  */
  for(i=1;i<N;i++){
    //@ assert 0 <= i < N;
    //@ assert (\forall integer j; 0 <= j < N ==> c[j] == 0);
    //@ assert(c[i] == 0);
  }
  return 0;
}
