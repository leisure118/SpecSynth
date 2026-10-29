#define INT_MAX 2147483647
/*@
  requires a <= 2147483647;
  ensures \result == a * 2;
  assigns \nothing;
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