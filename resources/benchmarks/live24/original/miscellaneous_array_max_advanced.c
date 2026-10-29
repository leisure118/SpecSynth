int array_max_advanced(int* arr, int n) {
    int max = arr[0];
    for (int i = 0; i < n; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    //@ assert \forall integer j; 0 <= j < n ==> arr[j] <= max;
    return max;
}