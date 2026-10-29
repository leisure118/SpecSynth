/*@
  requires n >= 0;
  requires \valid(a + (0 .. n-1));
  assigns \nothing;
*/
int arraysearch(int* a, int x, int n) { 
  /*@
    loop invariant 0 <= p <= n;
    loop assigns p;
    loop variant n - p;
  */
  for (int p = 0; p < n; p++) {
    if (x == a[p]) 
    //@ assert \exists integer k;  0 <= k <= p && x == a[k];
       return 1;
  }
  return 0;
} 