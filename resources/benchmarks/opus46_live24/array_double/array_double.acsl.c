/*@
  requires n >= 0;
  requires \valid(a+(0..n-1));
  assigns a[0..n-1];
  ensures \forall integer k; 0 <= k < n ==> a[k] == \old(a[k]) * 2;
*/
void arrayDouble(int *a, int n) {
    int p = 0;
    /*@
      loop invariant 0 <= p <= n;
      loop invariant \forall integer j; 0 <= j < p ==> a[j] == \at(a[j], Pre) * 2;
      loop invariant \forall integer j; p <= j < n ==> a[j] == \at(a[j], Pre);
      loop assigns p, a[0..n-1];
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