/*@
  requires n >= 0;
  requires \valid(a + (0 .. n-1));
  requires \forall integer i; 0 <= i < n-1 ==> a[i] <= a[i+1];
  assigns \nothing;
  ensures -1 <= \result < n;
  ensures \result >= 0 ==> a[\result] == x;
  ensures \result == -1 ==> \forall integer i; 0 <= i < n ==> a[i] != x;
*/
int binarysearch(int* a, int x, int n) {

    int low = -1;
    int high = n;
    int p;
    //@ admit \forall integer i, j; 0 <= i <= j < n ==> a[i] <= a[j];

    /*@
      loop invariant -1 <= low < high <= n;
      loop invariant \forall integer i; 0 <= i <= low ==> a[i] < x;
      loop invariant \forall integer i; high <= i < n ==> a[i] > x;
      loop assigns low, high, p;
      loop variant high - low;
    */
    while (low+1 < high) {
        p = (low + high) / 2;
        if (a[p] == x)
            return p;
        else
            if (a[p] < x)
            low = p;
            else high = p;
    }
    return -1;
}

// write a test
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int sum = binarysearch(arr, 3, 5);
    //@ assert arr[sum] == 3;
}