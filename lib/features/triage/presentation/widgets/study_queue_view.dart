import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../state/triage_state_manager.dart';

class StudyQueueView extends StatelessWidget {
  const StudyQueueView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<TriageStateManager>(
      builder: (context, stateManager, child) {
        if (stateManager.queue.isEmpty) {
          return const Center(
            child: Text("No active screenings in the camp queue."),
          );
        }

        return ListView.builder(
          itemCount: stateManager.queue.length,
          itemBuilder: (context, index) {
            final screening = stateManager.queue[index];
            final isHighRisk = screening.isHighRisk;

            return Card(
              color: isHighRisk ? Colors.red.shade100 : Colors.white,
              margin: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
              child: ListTile(
                leading: Icon(
                  isHighRisk ? Icons.warning_amber_rounded : Icons.person_outline,
                  color: isHighRisk ? Colors.red.shade900 : Colors.blueGrey,
                  size: 32.0,
                ),
                title: Text(
                  screening.fullName,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: isHighRisk ? Colors.red.shade900 : Colors.black87,
                  ),
                ),
                subtitle: Text("Jan Aadhaar: ${screening.janAadhaarNumber}\nRisk Index: ${screening.riskIndexScore.toStringAsFixed(1)}"),
                trailing: Chip(
                  label: Text(
                    screening.clinicalFlag,
                    style: TextStyle(
                      color: isHighRisk ? Colors.white : Colors.black87,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  backgroundColor: isHighRisk ? Colors.red.shade900 : Colors.grey.shade300,
                ),
              ),
            );
          },
        );
      },
    );
  }
}
