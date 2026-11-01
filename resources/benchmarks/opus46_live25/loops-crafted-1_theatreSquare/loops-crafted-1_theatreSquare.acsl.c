#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
/*@
  requires 1 <= a <= 109;
  requires 1 <= n <= 109;
  requires 1 <= m <= 109;
  assigns \nothing;
  ensures \result == ((n + a - 1) / a) * ((m + a - 1) / a);
*/
int correct_version(int n, int m, int a)
{
    int i = 0, j = 0, b = 0, l = 0;
    /*@
      loop invariant b == i * a;
      loop invariant i >= 0;
      loop invariant i == 0 || (i - 1) * a < n;
      loop assigns b, i;
      loop variant n - b;
    */
    while(b < n)
    {
        b = b + a;
        i = i + 1;
    }
    //@ assert i >= 1;
    //@ assert i * a >= n;
    //@ assert (i - 1) * a < n;
    //@ assert i == (n + a - 1) / a;
    /*@
      loop invariant l == j * a;
      loop invariant j >= 0;
      loop invariant j == 0 || (j - 1) * a < m;
      loop assigns l, j;
      loop variant m - l;
    */
    while(l < m)
    {
        l = l + a;
        j = j + 1;
    }
    //@ assert j >= 1;
    //@ assert j * a >= m;
    //@ assert (j - 1) * a < m;
    //@ assert j == (m + a - 1) / a;
    int x = 0, y = 0;
    /*@
      loop invariant y == x * j;
      loop invariant 0 <= x <= i;
      loop assigns x, y;
      loop variant i - x;
    */
    while(x < i)
    {
        y = y + j;
        x = x + 1;
    }
    //@ assert y == i * j;
    return y;
}
/*@
  requires 1 <= a <= 109;
  requires 1 <= n <= 109;
  requires 1 <= m <= 109;
  assigns \nothing;
  ensures \result == ((n + a - 1) / a) * ((m + a - 1) / a);
*/
int student_version(int n, int m, int a)
{
    int i = 0, j = 0, b = 0, l = 0;
    /*@
      loop invariant b == i * a;
      loop invariant i >= 0;
      loop invariant i == 0 || (i - 1) * a < n;
      loop assigns b, i;
      loop variant n - b;
    */
    while(b < n)
    {
        b = b + a;
        i = i + 1;
    }
    //@ assert i >= 1;
    //@ assert i * a >= n;
    //@ assert (i - 1) * a < n;
    //@ assert i == (n + a - 1) / a;
    /*@
      loop invariant l == j * a;
      loop invariant j >= 0;
      loop invariant j == 0 || (j - 1) * a < m;
      loop assigns l, j;
      loop variant m - l;
    */
    while(l < m)
    {
        l = l + a;
        j = j + 1;
    }
    //@ assert j >= 1;
    //@ assert j * a >= m;
    //@ assert (j - 1) * a < m;
    //@ assert j == (m + a - 1) / a;
    int x = 0, y = 0;
    /*@
      loop invariant y == x * j;
      loop invariant 0 <= x <= i;
      loop assigns x, y;
      loop variant i - x;
    */
    while(x < i)
    {
        y = y + j;
        x = x + 1;
    }
    //@ assert y == i * j;
    return y;
}
int main()
{
    int a=unknown(), n=unknown(), m=unknown();
    int n_stones1, n_stones2=unknown();
    n_stones1 = n_stones2;
    if((1 <= n) &&
       (1 <= m) &&
       (1 <= a) &&
       (n <= 109) &&
       (m <= 109) &&
       (a <= 109))
    {
        n_stones1 = correct_version(n, m, a);
        n_stones2 = student_version(n, m, a);
    }
    //@ assert(n_stones1 == n_stones2);
    return 0;
}
