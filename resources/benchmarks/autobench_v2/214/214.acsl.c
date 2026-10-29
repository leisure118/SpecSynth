// This program used an advanced ACSL clause: \max()
// Note: Some versions of 'wp' plugin may not support the \lambda clause.
//       The program may not verify in every machine.

/*@
  requires \valid(arr+(0 .. n-1));
  requires n > 0;
  ensures \forall integer j; 0 <= j < n ==> \result >= arr[j];
  assigns \nothing;
*/
int array_max_advanced(int* arr, int n) {
    int max = arr[0];
    /*@
      loop invariant 0 <= i <= n;
      loop invariant \forall integer j; 0 <= j < i ==> max >= arr[j];
      loop assigns i, max;
      loop variant n - i;
    */
    for (int i = 0; i < n; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}

// write a test
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int max = array_max_advanced(arr, 5);
    //@ assert max >= arr[0];
    //@ assert max >= arr[1];
    //@ assert max >= arr[2];
    //@ assert max >= arr[3];
    //@ assert max >= arr[4];
}