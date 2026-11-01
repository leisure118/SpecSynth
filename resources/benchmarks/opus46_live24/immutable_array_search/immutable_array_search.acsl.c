/*@
  requires n >= 0;
  requires \valid_read(a + (0 .. n-1));
  assigns \nothing;
  ensures \result == 0 || \result == 1;
  ensures (\exists integer i; 0 <= i < n && a[i] == x) ==> \result == 1;
  ensures (\forall integer i; 0 <= i < n ==> a[i] != x) ==> \result == 0;
*/
int arraysearch(int* a, int x, int n) { 
  /*@
    loop invariant 0 <= p <= n;
    loop invariant \forall integer j; 0 <= j < p ==> a[j] != x;
    loop assigns p;
    loop variant n - p;
  */
  for (int p = 0; p < n; p++) {
    if (x == a[p]) 
       return 1;
  }
  return 0;
}
void main() {
  int arr[5] = {1, 2, 3, 4, 5};
  int sum = arraysearch(arr, 3, 5);
  //@ assert sum == 1;
}