/*@
  requires \valid(&arr[n1]);
  requires \valid(&arr[n2]);
  requires n1 >= 0 && n1 < n;
  requires n2 >= 0 && n2 < n;
  assigns arr[n1], arr[n2];
  ensures arr[n1] == \old(arr[n2]);
  ensures arr[n2] == \old(arr[n1]);
*/
void array_swap(int* arr, int n, int n1, int n2) {
    int temp = arr[n1];
    arr[n1] = arr[n2];
    arr[n2] = temp;
}
int main(){
    int arr[] = {1, 2, 3, 4, 5};
    array_swap(arr, 5, 1, 3);
    //@ assert arr[1] == 4;
    //@ assert arr[3] == 2;
}