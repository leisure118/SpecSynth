/*@
  logic integer gcd(integer a, integer b) = 
      (a==0)?b:
      (b==0)?a:
      (a==b)?a:
      (a>b)? gcd(a-b, b) : gcd(a, b-a);
*/
int gcd(int a, int b) {
    if (a == 0)
       return b;
    if (b == 0)
       return a;
    if (a == b)
        return a;
    if (a > b)
        return gcd(a-b, b);
    return gcd(a, b-a);
}
int main()
{
    int a = 98, b = 56;
    int c = gcd(a, b);
    //@ assert c == 14;
    return 0;
}