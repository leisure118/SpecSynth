/*@
  requires n > 0;
  requires \valid_read(a+(0..n-1));
  requires \forall integer i, j; 0 <= i <= j < n ==> a[i] <= a[j];
  ensures \result == -1 || (0 <= \result < n && a[\result] == x);
  ensures \result == -1 ==> (\forall integer i; 0 <= i < n ==> a[i] != x);
  assigns \nothing;
*/
int binarysearch(int* a, int x, int n) {

    int low = -1;
    int high = n;
    int p;

    /*@
      loop invariant -1 <= low;
      loop invariant high <= n;
      loop invariant low < high;
      loop invariant \forall integer i; 0 <= i < n && a[i] == x ==> low < i < high;
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
