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
  for(i=0;i<N;i++) {
    x = unknown();
    //@ assert (x > -100000 && x < 100000);
    a[i]=x;
    b[i]=-x;
  }
  for(i=0;i<N;i++){
    c[i]=a[i]+b[i];
  }
  for(i=1;i<N;i++){
    //@ assert(c[i] == 0);
  }
  return 0;
}
