/*@ logic integer asum(int *a, integer n) =
      n <= 0 ? 0 : asum(a, n-1) + a[n-1]; */

/*@
  requires n >= 0;
  requires \valid_read(a+(0..n-1));
  assigns \nothing;
  ensures \result == asum(a, n);
*/
int sumArray(int *a, int n) {
    int p = 0, sum = 0;

    /*@
      loop invariant 0 <= p <= n;
      loop invariant sum == asum(a, p);
      loop assigns p, sum;
      loop variant n - p;
    */
    while (p < n) {
        sum = sum + a[p];
        p++;
    }
    return sum;
}

// write a test
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int sum = sumArray(arr, 5);
    //@ assert sum == 15;
}
