#include <stdio.h>

/*@
  requires n > 0;
  requires \valid(a + (0 .. n-1));
  assigns a[0 .. n-1];
  ensures \forall integer k; 0 <= k < n-1 ==> a[k] <= a[k+1];
*/
void bubbleSort(int *a, int n) {
    if (n <= 0) return;
    int i, j, temp;

    /*@
      loop invariant 0 <= i <= n-1;
      loop invariant \forall integer k; i <= k < n-1 ==> a[k] <= a[k+1];
      loop invariant i+1 < n ==> \forall integer k; 0 <= k <= i ==> a[k] <= a[i+1];
      loop assigns i, j, temp, a[0 .. n-1];
      loop variant i;
    */
    for(i=n-1; i>0; i--) {
        /*@
          loop invariant 0 <= j <= i;
          loop invariant \forall integer k; 0 <= k < j ==> a[k] <= a[j];
          loop invariant \forall integer k; i+1 <= k < n-1 ==> a[k] <= a[k+1];
          loop invariant i+1 < n ==> \forall integer k; 0 <= k <= i ==> a[k] <= a[i+1];
          loop assigns j, temp, a[0 .. i];
          loop variant i - j;
        */
        for(j=0; j<i; j++) {
            if (a[j] > a[j+1]) {
                temp = a[j];
                a[j] = a[j+1];
                a[j+1] = temp;
            }
        }
    }
}

// write a test
void main() {
    int arr[5] = {5, 4, 3, 2, 1};
    bubbleSort(arr, 5);
    //@ assert \forall int i; 0 <= i < 4 ==> arr[i] <= arr[i+1];
}