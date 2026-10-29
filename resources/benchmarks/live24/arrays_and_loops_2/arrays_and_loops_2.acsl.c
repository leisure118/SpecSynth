/*@
  requires n >= 1;
  requires \valid(a + (0 .. n-1));
  assigns \nothing;
  ensures \forall integer k; 0 <= k < n ==> \result >= a[k];
*/
int arraymax(int* a, int n) {
  int i = 1;
  int max = a[0];
  /*@
    loop invariant 1 <= i <= n;
    loop invariant \forall integer k; 0 <= k < i ==> max >= a[k];
    loop assigns i, max;
    loop variant n - i;
  */
  while (i < n) {
    if (max < a[i])
    max = a[i];
    i = i + 1;
  }
  //@ assert \forall integer k;  0 <= k < n ==> max >=  a[k];
  return max;
}  