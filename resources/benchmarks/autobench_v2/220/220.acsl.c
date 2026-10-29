/*@
  requires \valid(a + (0 .. n-1));
  requires n >= 0;
  assigns a[0 .. n-1];
  ensures \forall integer k; 0 <= k < n ==> a[k] == \old(a[n-1-k]);
*/
void reverse(int *a, int n) {
    int i = 0;
    int j = n-1;

    /*@
      loop invariant 0 <= i <= n/2;
      loop invariant j == n-1-i;
      loop invariant \forall integer k; 0 <= k < i ==> a[k] == \at(a[n-1-k], LoopEntry);
      loop invariant \forall integer k; 0 <= k < i ==> a[n-1-k] == \at(a[k], LoopEntry);
      loop invariant \forall integer k; i <= k < n-i ==> a[k] == \at(a[k], LoopEntry);
      loop assigns i, j, a[0 .. n-1];
      loop variant n/2 - i;
    */
    while (i < n/2) {
        int temp = a[i];
        a[i] = a[j];
        a[j] = temp;
        i++;
        j--;
    }
}

// write a test
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    reverse(arr, 5);
    //@ assert arr[4] == 1;
}
