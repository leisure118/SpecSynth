#define INT_MAX 2147483647
/*@
  requires a <= 2147483647;
  assigns \nothing;
  ensures \result == 2 * a;
*/
unsigned lshift(unsigned a)
{
	return a << 1;
}
int main() {
    unsigned a = 5;
    unsigned result = lshift(a);
    //@ assert result == 10;
    return 0;
}