#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
/*@
  requires a > 0;
  requires n >= 0;
  requires m >= 0;
  assigns \nothing;
  ensures \result == ((n + a - 1) / a) * ((m + a - 1) / a);
*/
int correct_version(int n, int m, int a)
{
    int i = 0, j = 0, b = 0, l = 0;
    /*@
      loop invariant 0 <= i;
      loop invariant b == i * a;
      loop invariant b < n + a;
      loop assigns i, b;
      loop variant n - b;
    */
    while(b < n)
    {
        b = b + a;
        i = i + 1;
    }
    /*@
      loop invariant 0 <= j;
      loop invariant l == j * a;
      loop invariant l < m + a;
      loop assigns j, l;
      loop variant m - l;
    */
    while(l < m)
    {
        l = l + a;
        j = j + 1;
    }
    int x = 0, y = 0;
    /*@
      loop invariant 0 <= x <= i;
      loop invariant y == x * j;
      loop assigns x, y;
      loop variant i - x;
    */
    while(x < i)
    {
        y = y + j;
        x = x + 1;
    }
    return y;
}
/*@
  requires a > 0;
  requires n >= 0;
  requires m >= 0;
  assigns \nothing;
  ensures \result == ((n + a - 1) / a) * ((m + a - 1) / a);
*/
int student_version(int n, int m, int a)
{
    int i = 0, j = 0, b = 0, l = 0;
    /*@
      loop invariant 0 <= i;
      loop invariant b == i * a;
      loop invariant b < n + a;
      loop assigns i, b;
      loop variant n - b;
    */
    while(b < n)
    {
        b = b + a;
        i = i + 1;
    }
    /*@
      loop invariant 0 <= j;
      loop invariant l == j * a;
      loop invariant l < m + a;
      loop assigns j, l;
      loop variant m - l;
    */
    while(l < m)
    {
        l = l + a;
        j = j + 1;
    }
    int x = 0, y = 0;
    /*@
      loop invariant 0 <= x <= i;
      loop invariant y == x * j;
      loop assigns x, y;
      loop variant i - x;
    */
    while(x < i)
    {
        y = y + j;
        x = x + 1;
    }
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
