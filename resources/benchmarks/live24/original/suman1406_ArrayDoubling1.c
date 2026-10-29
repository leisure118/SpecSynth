void arraydouble(int *a, int n)
{
    for (int p = 0; p < n; p++)
    {
        a[p] = a[p] * 2;
    }
}
int main(){
    int a[] = {0, 1, 2, 3, 4};
    int n = sizeof(a) / sizeof(a[0]);
    //@ assert \forall integer k; 0 <= k < n ==> a[k] == k;
    arraydouble(a, 5);
    //@ assert a[0] == 0 && a[1] == 2 && a[2] == 4 && a[3] == 6 && a[4] == 8;
    return 0;
}