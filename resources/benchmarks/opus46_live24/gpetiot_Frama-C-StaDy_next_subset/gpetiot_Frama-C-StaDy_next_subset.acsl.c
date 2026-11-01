/*@ 
predicate is_dset{L}(int *a, integer n) =
  \forall integer i; 0 <= i < n ==> (a[i] == 0 || a[i] == 1);
predicate is_eq{L1,L2}(int *a, integer n) =
  \forall integer i; 0 <= i < n ==> \at(a[i],L1) == \at(a[i],L2);
predicate lt{L1,L2}(int* a, integer i) =
  \at(a[i],L1) < \at(a[i],L2); 
*/
/*@
  requires n >= 1;
  requires \valid(s+(0..n-1));
  requires is_dset(s, n);
  assigns s[0 .. n-1];
*/
int nextSubset(int s[], int n) {
  int i,k;
  /*@
    loop invariant -1 <= k <= n-1;
    loop invariant \forall integer j; k < j < n ==> s[j] == 1;
    loop invariant is_dset(s, n);
    loop assigns k;
    loop variant k + 1;
  */
  for (k = n-1; k >= 0; k--) { if (s[k] == 0) { break; } }
  if (k == -1) { return -1; }
  s[k] = 1;
  /*@
    loop invariant k+1 <= i <= n;
    loop invariant \forall integer j; 0 <= j <= k ==> (s[j] == 0 || s[j] == 1);
    loop invariant \forall integer j; k+1 <= j < i ==> s[j] == 0;
    loop invariant \forall integer j; i <= j < n ==> (s[j] == 0 || s[j] == 1);
    loop assigns i, s[k+1 .. n-1];
    loop variant n - i;
  */
  for (i = k+1; i < n; i++) { s[i] = 0; }
  //@ assert is_dset(s,n);
  return k;
}