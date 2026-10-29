int arraysearch(int* a, int x, int n) { 
  for (int p = 0; p < n; p++) {
    if (x == a[p]) 
    //@ assert \exists integer k;  0 <= k <= p && x == a[k];
       return 1;
  }
  return 0;
} 