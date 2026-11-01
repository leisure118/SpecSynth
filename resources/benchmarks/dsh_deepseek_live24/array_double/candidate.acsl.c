/*@
  requires n >= 0;
  requires \valid(a + (0 .. n-1));
  requires \valid_read(a + (0 .. n-1));
  requires \forall integer j; 0 <= j < n ==> -1073741824 <= a[j] <= 1073741823;
  assigns a[0 .. n-1];
  ensures \forall integer j; 0 <= j < n ==> a[j] == 2 * \old(a[j]);
*/
void arrayDouble(int *a, int n) {
    int p = 0;
    /*@
      loop invariant 0 <= p <= n;
      loop invariant \forall integer j; 0 <= j < p ==> a[j] == 2 * \at(a[j], Pre);
      loop invariant \forall integer j; p <= j < n ==> a[j] == \at(a[j], Pre);
      loop assigns p, a[0 .. n-1];
      loop variant n - p;
    */
    while (p < n) {
        a[p] = a[p] * 2;
        p = p + 1;
    } 
}
int main() {
    int arr[] = {0,1,2,3,4,5};
    arrayDouble(arr, 6);
    //@ assert \forall integer k; 0 <= k < 6 ==> arr[k] == 2*k;
}
