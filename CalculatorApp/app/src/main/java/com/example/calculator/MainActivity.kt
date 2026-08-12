package com.example.calculator

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme()
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    CalculatorApp()
                }
            }
        }
    }
}

private fun formatNumber(value: Double): String {
    if (value.isNaN()) return "错误"
    if (value.isInfinite()) return if (value > 0) "∞" else "-∞"
    val longValue = value.toLong()
    return if (value == longValue.toDouble()) {
        longValue.toString()
    } else {
        String.format("%.8f", value).trimEnd('0').trimEnd('.')
    }
}

private fun calculate(a: Double, b: Double, op: String): Double {
    return when (op) {
        "+" -> a + b
        "-" -> a - b
        "×" -> a * b
        "÷" -> if (b != 0.0) a / b else Double.NaN
        else -> b
    }
}

@Composable
fun CalculatorApp() {
    var display by remember { mutableStateOf("0") }
    var previousValue by remember { mutableStateOf<Double?>(null) }
    var operator by remember { mutableStateOf<String?>(null) }
    var waitForNewNumber by remember { mutableStateOf(false) }

    fun inputNumber(num: String) {
        if (waitForNewNumber) {
            display = num
            waitForNewNumber = false
        } else {
            display = if (display == "0") num else display + num
        }
    }

    fun inputDecimal() {
        if (waitForNewNumber) {
            display = "0."
            waitForNewNumber = false
            return
        }
        if (!display.contains(".")) {
            display += "."
        }
    }

    fun clearAll() {
        display = "0"
        previousValue = null
        operator = null
        waitForNewNumber = false
    }

    fun toggleSign() {
        if (display != "0") {
            display = if (display.startsWith("-")) {
                display.substring(1)
            } else {
                "-$display"
            }
        }
    }

    fun percent() {
        val value = display.toDoubleOrNull() ?: return
        display = formatNumber(value / 100.0)
    }

    fun performOperator(op: String) {
        val currentValue = display.toDoubleOrNull() ?: return

        if (previousValue == null) {
            previousValue = currentValue
        } else if (!waitForNewNumber && operator != null) {
            val result = calculate(previousValue!!, currentValue, operator!!)
            display = formatNumber(result)
            previousValue = result
        }

        operator = op
        waitForNewNumber = true
    }

    fun equalsAction() {
        val currentValue = display.toDoubleOrNull() ?: return
        if (previousValue != null && operator != null) {
            val result = calculate(previousValue!!, currentValue, operator!!)
            display = formatNumber(result)
            previousValue = null
            operator = null
            waitForNewNumber = true
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1C1C1E))
            .padding(16.dp),
        verticalArrangement = Arrangement.Bottom
    ) {
        Text(
            text = display,
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            fontSize = 72.sp,
            fontWeight = FontWeight.Light,
            color = Color.White,
            textAlign = TextAlign.End,
            maxLines = 2
        )

        Spacer(modifier = Modifier.height(16.dp))

        val buttons = listOf(
            listOf(
                ButtonSpec("AC", Color(0xFFA5A5A5), Color.Black, ::clearAll),
                ButtonSpec("±", Color(0xFFA5A5A5), Color.Black, ::toggleSign),
                ButtonSpec("%", Color(0xFFA5A5A5), Color.Black, ::percent),
                ButtonSpec("÷", Color(0xFFFF9F0A), Color.White, { performOperator("÷") })
            ),
            listOf(
                ButtonSpec("7", Color(0xFF333333), Color.White, { inputNumber("7") }),
                ButtonSpec("8", Color(0xFF333333), Color.White, { inputNumber("8") }),
                ButtonSpec("9", Color(0xFF333333), Color.White, { inputNumber("9") }),
                ButtonSpec("×", Color(0xFFFF9F0A), Color.White, { performOperator("×") })
            ),
            listOf(
                ButtonSpec("4", Color(0xFF333333), Color.White, { inputNumber("4") }),
                ButtonSpec("5", Color(0xFF333333), Color.White, { inputNumber("5") }),
                ButtonSpec("6", Color(0xFF333333), Color.White, { inputNumber("6") }),
                ButtonSpec("-", Color(0xFFFF9F0A), Color.White, { performOperator("-") })
            ),
            listOf(
                ButtonSpec("1", Color(0xFF333333), Color.White, { inputNumber("1") }),
                ButtonSpec("2", Color(0xFF333333), Color.White, { inputNumber("2") }),
                ButtonSpec("3", Color(0xFF333333), Color.White, { inputNumber("3") }),
                ButtonSpec("+", Color(0xFFFF9F0A), Color.White, { performOperator("+") })
            ),
            listOf(
                ButtonSpec("0", Color(0xFF333333), Color.White, { inputNumber("0") }, true),
                ButtonSpec(".", Color(0xFF333333), Color.White, ::inputDecimal),
                ButtonSpec("=", Color(0xFFFF9F0A), Color.White, ::equalsAction)
            )
        )

        buttons.forEach { row ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 6.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                row.forEach { btn ->
                    CalcButton(
                        text = btn.text,
                        backgroundColor = btn.backgroundColor,
                        textColor = btn.textColor,
                        isWide = btn.isWide,
                        onClick = btn.onClick
                    )
                }
            }
        }
    }
}

private data class ButtonSpec(
    val text: String,
    val backgroundColor: Color,
    val textColor: Color,
    val onClick: () -> Unit,
    val isWide: Boolean = false
)

@Composable
private fun RowScope.CalcButton(
    text: String,
    backgroundColor: Color,
    textColor: Color,
    isWide: Boolean = false,
    onClick: () -> Unit
) {
    val baseModifier = Modifier
        .clip(if (isWide) RoundedCornerShape(50) else CircleShape)
        .background(backgroundColor)
        .aspectRatio(if (isWide) 2f else 1f)

    val finalModifier = if (isWide) {
        Modifier.fillMaxWidth(0.5f).then(baseModifier)
    } else {
        Modifier.weight(1f).then(baseModifier)
    }

    Button(
        onClick = onClick,
        modifier = finalModifier,
        colors = ButtonDefaults.buttonColors(
            containerColor = Color.Transparent,
            contentColor = textColor
        ),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp)
    ) {
        Text(
            text = text,
            fontSize = if (text.length > 1) 28.sp else 34.sp,
            fontWeight = FontWeight.Medium,
            color = textColor
        )
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
private fun CalculatorPreview() {
    MaterialTheme(
        colorScheme = darkColorScheme()
    ) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background
        ) {
            CalculatorApp()
        }
    }
}
