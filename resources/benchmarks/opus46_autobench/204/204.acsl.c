/*@
  requires n >= 0;
  requires \valid(a+(0..n-1));
  assigns \nothing;
  ensures (\exists integer i; 0 <= i < n && a[i] == x) ==> \result == 1;
  ensures (\forall integer i; 0 <= i < n ==> a[i] != x) ==> \result == 0;
*/
int arraySearch(int *a, int x, int n) {
    int p = 0;

    /*@
      loop invariant 0 <= p <= n;
      loop invariant \forall integer j; 0 <= j < p ==> a[j] != x;
      loop assigns p;
      loop variant n - p;
    */
    while (p < n) {
        if (a[p] == x) {
            return 1;
        }
        p++;
    }
    return 0;
}

// write a test
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int sum = arraySearch(arr, 3, 5);
    //@ assert sum == 1;
}
