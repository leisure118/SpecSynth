#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int correct_version(int n, int m, int a)
{
    int i = 0, j = 0, b = 0, l = 0;
    while(b < n)
    {
        b = b + a;
        i = i + 1;
    }
    while(l < m)
    {
        l = l + a;
        j = j + 1;
    }
    int x = 0, y = 0;
    while(x < i)
    {
        y = y + j;
        x = x + 1;
    }
    return y;
}
int student_version(int n, int m, int a)
{
    int i = 0, j = 0, b = 0, l = 0;
    while(b < n)
    {
        b = b + a;
        i = i + 1;
    }
    while(l < m)
    {
        l = l + a;
        j = j + 1;
    }
    int x = 0, y = 0;
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
