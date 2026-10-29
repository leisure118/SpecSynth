// Program to swap 2 elements of an array at the givem indices n1, n2

/*@
  requires n >= 0;
  requires 0 <= n1 < n;
  requires 0 <= n2 < n;
  requires \valid(arr + (0 .. n-1));
  assigns arr[n1], arr[n2];
  ensures arr[n1] == \old(arr[n2]);
  ensures arr[n2] == \old(arr[n1]);
  ensures \forall integer k; 0 <= k < n && k != n1 && k != n2 ==> arr[k] == \old(arr[k]);
*/
void array_swap(int* arr, int n, int n1, int n2) {
    int temp = arr[n1];
    arr[n1] = arr[n2];
    arr[n2] = temp;
}

// write a test
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    array_swap(arr, 5, 0, 4);
    //@ assert arr[0] == 5;
    //@ assert arr[1] == 2;
    //@ assert arr[2] == 3;
    //@ assert arr[3] == 4;
    //@ assert arr[4] == 1;
}