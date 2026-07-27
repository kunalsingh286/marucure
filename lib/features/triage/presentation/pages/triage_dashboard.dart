import 'package:flutter/material.dart';
import '../widgets/study_queue_view.dart';

class TriageDashboard extends StatelessWidget {
  const TriageDashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('MaruCure Silicosis Triage Engine Field Client'),
        backgroundColor: Colors.blueGrey.shade900,
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          // Responsive Multi-Surface Compilation Layouts
          // If the screen width expands to match a standard Windows administrative laptop
          if (constraints.maxWidth >= 800) {
            return Row(
              children: [
                // Queue pane
                const Expanded(
                  flex: 1,
                  child: StudyQueueView(),
                ),
                // Divider
                const VerticalDivider(width: 1, color: Colors.grey),
                // Diagnostic detail summary pane
                Expanded(
                  flex: 2,
                  child: Center(
                    child: Text(
                      'Select a screening to view diagnostic details.',
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                  ),
                ),
              ],
            );
          }
          
          // Compact list-view grid for rugged Android field tablet aspect ratio
          return const StudyQueueView();
        },
      ),
    );
  }
}
